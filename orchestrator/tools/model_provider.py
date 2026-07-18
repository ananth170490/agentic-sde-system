from __future__ import annotations

import json
import os
from enum import Enum
from types import UnionType
from typing import Any, TypeVar, Union, get_args, get_origin
from urllib import error, request

from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError


ModelT = TypeVar("ModelT", bound=BaseModel)


class _StructuredOutputMixin:
	def _complete_structured_with_retry(
		self,
		system_prompt: str,
		user_prompt: str,
		response_model: type[ModelT],
	) -> ModelT:
		schema_json = json.dumps(response_model.model_json_schema(), indent=2)
		example_json = json.dumps(self._example_from_schema(response_model.model_json_schema()), indent=2)
		base_instruction = (
			"Return JSON only. Do not include markdown or extra text. "
			"Return an instance object, not a JSON schema. "
			"The JSON must match this schema exactly:\n"
			f"{schema_json}\n\n"
			"Example output shape (fill with real values, do not copy literally unless correct):\n"
			f"{example_json}"
		)

		first_attempt_prompt = f"{user_prompt}\n\n{base_instruction}"
		try:
			first_response = self._invoke(system_prompt=system_prompt, user_prompt=first_attempt_prompt)
		except Exception as err:
			return self._fallback_model_instance(
				response_model=response_model,
				failure_reason=str(err),
				source_prompt=user_prompt,
			)

		try:
			return self._parse_response(first_response, response_model)
		except (json.JSONDecodeError, ValidationError) as err:
			correction_prompt = (
				f"{user_prompt}\n\n"
				"Your previous response could not be validated. "
				"Fix it and return JSON only that exactly matches the schema.\n"
				f"Validation/parsing error:\n{err}\n\n"
				f"Required schema:\n{schema_json}"
			)
			try:
				second_response = self._invoke(system_prompt=system_prompt, user_prompt=correction_prompt)
			except Exception as second_err:
				return self._fallback_model_instance(
					response_model=response_model,
					failure_reason=str(second_err),
					source_prompt=user_prompt,
				)
			return self._parse_response(second_response, response_model)

	def _fallback_model_instance(self, response_model: type[ModelT], failure_reason: str, source_prompt: str) -> ModelT:
		example_payload = self._example_from_schema(response_model.model_json_schema())
		if response_model.__name__ == "RequirementSpec":
			example_payload["category"] = "ambiguous"
			example_payload["ambiguity_score"] = 0.9
			example_payload["raw_text"] = source_prompt[:300]
			example_payload["explicit_requirements"] = ["Clarify and scope requirement before implementation"]
			example_payload["implicit_requirements"] = [
				"Maintain current system behavior while gathering missing constraints"
			]
		if response_model.__name__ == "TaskDAG":
			example_payload = {"tasks": []}
		fallback_payload = self._inject_fallback_reason(example_payload, failure_reason)
		return response_model.model_validate(self._coerce_payload_for_model(fallback_payload, response_model))

	def _inject_fallback_reason(self, payload: Any, failure_reason: str) -> Any:
		if not isinstance(payload, dict):
			return payload

		reason = self._humanize_failure_reason(failure_reason)
		if "ambiguities" in payload and isinstance(payload["ambiguities"], list):
			payload["ambiguities"] = [reason]
		if "implicit_requirements" in payload and isinstance(payload["implicit_requirements"], list):
			payload["implicit_requirements"] = [reason]
		if "tradeoffs" in payload and isinstance(payload["tradeoffs"], list):
			payload["tradeoffs"] = [reason]
		if "risks" in payload and isinstance(payload["risks"], list):
			payload["risks"] = [reason]
		if "final_summary" in payload and isinstance(payload["final_summary"], str):
			payload["final_summary"] = (
				"## Implementation Plan and Rationale\n"
				f"{reason}\n\n"
				"## Generated Artifacts\n"
				"- No artifacts recorded\n\n"
				"## Risks, Trade-offs, and Validation Approach\n"
				f"- {reason}\n\n"
				"## Assumptions and Limitations\n"
				"- Fallback output was synthesized from schema defaults.\n"
			)
		return payload

	def _humanize_failure_reason(self, failure_reason: str) -> str:
		normalized = (failure_reason or "").strip()
		lowered = normalized.lower()

		if "402" in lowered or "payment required" in lowered:
			return (
				"Provider fallback used because the model provider request was blocked by quota/billing limits. "
				"Check provider credits and retry the run."
			)
		if "401" in lowered or "unauthorized" in lowered or "forbidden" in lowered:
			return (
				"Provider fallback used because model provider credentials were rejected. "
				"Verify API key configuration and retry the run."
			)
		if "network" in lowered or "timed out" in lowered or "timeout" in lowered:
			return (
				"Provider fallback used because the model provider was temporarily unreachable. "
				"Retry once connectivity is restored."
			)

		return "Provider fallback used due to upstream model provider unavailability. Retry the run once provider access is restored."

	def _parse_response(self, raw_text: str, response_model: type[ModelT]) -> ModelT:
		payload = json.loads(self._extract_json(raw_text))
		try:
			return response_model.model_validate(payload)
		except ValidationError:
			coerced_payload = self._coerce_payload_for_model(payload, response_model)
			return response_model.model_validate(coerced_payload)

	def _coerce_payload_for_model(self, payload: Any, response_model: type[ModelT]) -> Any:
		if isinstance(payload, list):
			field_names = list(response_model.model_fields.keys())
			if len(field_names) == 1:
				field_name = field_names[0]
				field_info = response_model.model_fields[field_name]
				return {field_name: self._coerce_value(payload, field_info.annotation)}
			return payload

		if not isinstance(payload, dict):
			return payload

		coerced = dict(payload)
		for field_name, field_info in response_model.model_fields.items():
			if field_name not in coerced:
				continue
			coerced[field_name] = self._coerce_value(coerced[field_name], field_info.annotation)
		return coerced

	def _coerce_value(self, value: Any, annotation: Any) -> Any:
		origin = get_origin(annotation)

		if origin in (Union, UnionType):
			args = [arg for arg in get_args(annotation) if arg is not type(None)]
			if not args:
				return value
			return self._coerce_value(value, args[0])

		if origin is list:
			item_type = get_args(annotation)[0] if get_args(annotation) else Any
			items = value if isinstance(value, list) else [value]
			return [self._coerce_value(item, item_type) for item in items]

		if origin is dict:
			key_type, value_type = get_args(annotation) if get_args(annotation) else (Any, Any)
			if isinstance(value, list):
				coerced_dict: dict[Any, Any] = {}
				for index, item in enumerate(value):
					if isinstance(item, dict):
						raw_key = item.get("path") or item.get("file") or item.get("filename") or item.get("name")
						raw_value = item.get("content") or item.get("code") or item.get("text")
						if raw_key is not None and raw_value is not None:
							coerced_key = self._coerce_value(raw_key, key_type)
							coerced_dict[coerced_key] = self._coerce_value(raw_value, value_type)
							continue
					coerced_dict[self._coerce_value(f"item_{index}", key_type)] = self._coerce_value(item, value_type)
				return coerced_dict
			if isinstance(value, dict):
				return {
					self._coerce_value(k, key_type): self._coerce_value(v, value_type)
					for k, v in value.items()
				}

		if annotation is str:
			if isinstance(value, str):
				return value
			if isinstance(value, dict) and isinstance(value.get("name"), str):
				description = value.get("description")
				if isinstance(description, str) and description.strip():
					return f"{value['name']}: {description}"
				return value["name"]
			return json.dumps(value, ensure_ascii=True)

		if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, dict):
			return self._coerce_payload_for_model(value, annotation)

		if isinstance(annotation, type) and issubclass(annotation, Enum):
			for member in annotation:
				if value == member.value or value == member.name:
					return member.value
			return next(iter(annotation)).value

		return value

	def _extract_json(self, raw_text: str) -> str:
		text = raw_text.strip()
		if text.startswith("```"):
			lines = text.splitlines()
			if lines and lines[0].startswith("```"):
				lines = lines[1:]
			if lines and lines[-1].startswith("```"):
				lines = lines[:-1]
			text = "\n".join(lines).strip()

		start_object = text.find("{")
		start_array = text.find("[")
		start_candidates = [idx for idx in (start_object, start_array) if idx != -1]
		if not start_candidates:
			return text
		start = min(start_candidates)

		for open_char, close_char in (("{", "}"), ("[", "]")):
			if text[start] != open_char:
				continue
			depth = 0
			for idx in range(start, len(text)):
				char = text[idx]
				if char == open_char:
					depth += 1
				elif char == close_char:
					depth -= 1
					if depth == 0:
						return text[start : idx + 1]
		return text

	def _example_from_schema(self, schema: dict) -> dict:
		properties = schema.get("properties", {})
		defs = schema.get("$defs", {})
		example: dict[str, object] = {}
		for key, prop in properties.items():
			example[key] = self._example_value_for_property(prop, defs)
		return example

	def _example_value_for_property(self, prop: dict, defs: dict[str, Any]) -> object:
		if "$ref" in prop:
			resolved = self._resolve_schema_ref(prop["$ref"], defs)
			if resolved is not None:
				return self._example_value_for_property(resolved, defs)
			return "example"

		if "anyOf" in prop and isinstance(prop["anyOf"], list) and prop["anyOf"]:
			for option in prop["anyOf"]:
				if option.get("type") == "null":
					continue
				return self._example_value_for_property(option, defs)
			return None

		if "oneOf" in prop and isinstance(prop["oneOf"], list) and prop["oneOf"]:
			return self._example_value_for_property(prop["oneOf"][0], defs)

		prop_type = prop.get("type")
		if prop_type == "string":
			return "example"
		if prop_type == "number":
			return 0.5
		if prop_type == "integer":
			return 1
		if prop_type == "boolean":
			return True
		if prop_type == "array":
			items = prop.get("items", {})
			return [self._example_value_for_property(items, defs)]
		if prop_type == "object":
			properties = prop.get("properties")
			if isinstance(properties, dict) and properties:
				return {key: self._example_value_for_property(value, defs) for key, value in properties.items()}
			return {"key": "value"}
		if "enum" in prop and prop["enum"]:
			return prop["enum"][0]
		if "properties" in prop and isinstance(prop["properties"], dict):
			return {key: self._example_value_for_property(value, defs) for key, value in prop["properties"].items()}
		return "example"

	def _resolve_schema_ref(self, ref: Any, defs: dict[str, Any]) -> dict[str, Any] | None:
		if not isinstance(ref, str):
			return None
		prefix = "#/$defs/"
		if not ref.startswith(prefix):
			return None
		key = ref[len(prefix):]
		resolved = defs.get(key)
		if isinstance(resolved, dict):
			return resolved
		return None


class ModelProvider(_StructuredOutputMixin):
	def __init__(self, model_name: str = "claude-3-5-sonnet-latest") -> None:
		load_dotenv()
		api_key = os.getenv("ANTHROPIC_API_KEY")
		if not api_key:
			raise ValueError("ANTHROPIC_API_KEY is not set")

		self._client = Anthropic(api_key=api_key)
		self._model_name = model_name

	def complete_structured(
		self,
		system_prompt: str,
		user_prompt: str,
		response_model: type[ModelT],
	) -> ModelT:
		return self._complete_structured_with_retry(system_prompt, user_prompt, response_model)

	def _invoke(self, system_prompt: str, user_prompt: str) -> str:
		msg = self._client.messages.create(
			model=self._model_name,
			max_tokens=2048,
			system=system_prompt,
			messages=[{"role": "user", "content": user_prompt}],
		)

		text_blocks = [block.text for block in msg.content if getattr(block, "type", None) == "text"]
		return "\n".join(text_blocks).strip()


class OllamaModelProvider(_StructuredOutputMixin):
	def __init__(
		self,
		model_name: str = "llama3.2:3b",
		base_url: str = "http://127.0.0.1:11434",
	) -> None:
		self._model_name = model_name
		self._base_url = base_url.rstrip("/")

	def complete_structured(
		self,
		system_prompt: str,
		user_prompt: str,
		response_model: type[ModelT],
	) -> ModelT:
		return self._complete_structured_with_retry(system_prompt, user_prompt, response_model)

	def _invoke(self, system_prompt: str, user_prompt: str) -> str:
		payload = {
			"model": self._model_name,
			"prompt": f"System:\n{system_prompt}\n\nUser:\n{user_prompt}",
			"stream": False,
			"options": {"temperature": 0},
		}
		data = json.dumps(payload).encode("utf-8")
		req = request.Request(
			url=f"{self._base_url}/api/generate",
			data=data,
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		try:
			with request.urlopen(req) as response:
				body = response.read().decode("utf-8")
		except error.HTTPError as err:
			message = f"OpenRouter HTTP error {err.code}: {err.reason}"
			raise RuntimeError(message) from err
		except error.URLError as err:
			raise RuntimeError(f"OpenRouter network error: {err.reason}") from err
		parsed = json.loads(body)
		return str(parsed.get("response", "")).strip()


class OpenRouterModelProvider(_StructuredOutputMixin):
	def __init__(
		self,
		api_key: str,
		model_name: str = "openai/gpt-4o-mini",
		base_url: str = "https://openrouter.ai/api/v1",
		referer: str | None = None,
		title: str | None = None,
	) -> None:
		if not api_key:
			raise ValueError("OPENROUTER_API_KEY is not set")

		self._api_key = api_key
		self._model_name = model_name
		self._base_url = base_url.rstrip("/")
		self._referer = referer
		self._title = title

	def complete_structured(
		self,
		system_prompt: str,
		user_prompt: str,
		response_model: type[ModelT],
	) -> ModelT:
		return self._complete_structured_with_retry(system_prompt, user_prompt, response_model)

	def _invoke(self, system_prompt: str, user_prompt: str) -> str:
		payload = {
			"model": self._model_name,
			"messages": [
				{"role": "system", "content": system_prompt},
				{"role": "user", "content": user_prompt},
			],
			"temperature": 0,
		}

		headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {self._api_key}",
		}
		if self._referer:
			headers["HTTP-Referer"] = self._referer
		if self._title:
			headers["X-Title"] = self._title

		data = json.dumps(payload).encode("utf-8")
		req = request.Request(
			url=f"{self._base_url}/chat/completions",
			data=data,
			headers=headers,
			method="POST",
		)
		with request.urlopen(req) as response:
			body = response.read().decode("utf-8")

		parsed = json.loads(body)
		choices = parsed.get("choices", [])
		if not choices:
			return ""

		message = choices[0].get("message", {})
		content = message.get("content", "")

		if isinstance(content, str):
			return content.strip()

		if isinstance(content, list):
			parts: list[str] = []
			for part in content:
				if isinstance(part, dict) and part.get("type") == "text":
					text_value = part.get("text", "")
					if isinstance(text_value, str):
						parts.append(text_value)
			return "\n".join(parts).strip()

		return str(content).strip()


def build_model_provider_from_env() -> ModelProvider | OllamaModelProvider | OpenRouterModelProvider:
	load_dotenv()
	provider = os.getenv("MODEL_PROVIDER", "anthropic").strip().lower()
	if provider == "ollama":
		return OllamaModelProvider(
			model_name=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
			base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
		)
	if provider == "openrouter":
		return OpenRouterModelProvider(
			api_key=os.getenv("OPENROUTER_API_KEY", ""),
			model_name=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
			base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
			referer=os.getenv("OPENROUTER_HTTP_REFERER", "").strip() or None,
			title=os.getenv("OPENROUTER_X_TITLE", "").strip() or None,
		)
	return ModelProvider(model_name=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"))


class FakeModelProvider:
	def __init__(self, canned_response: BaseModel | dict | str) -> None:
		self._canned_response = canned_response

	def complete_structured(
		self,
		system_prompt: str,
		user_prompt: str,
		response_model: type[ModelT],
	) -> ModelT:
		del system_prompt, user_prompt

		if isinstance(self._canned_response, BaseModel):
			if isinstance(self._canned_response, response_model):
				return self._canned_response
			return response_model.model_validate(self._canned_response.model_dump())

		if isinstance(self._canned_response, dict):
			return response_model.model_validate(self._canned_response)

		if isinstance(self._canned_response, str):
			data = json.loads(self._canned_response)
			return response_model.model_validate(data)

		raise TypeError("Unsupported canned_response type for FakeModelProvider")
