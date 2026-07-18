from __future__ import annotations

import ast
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from orchestrator.state import ImpactedArea


@dataclass
class SymbolInfo:
	name: str
	docstring: str | None


class RepoIndex:
	def __init__(self) -> None:
		self.root_path: Path | None = None
		self.file_symbols: dict[str, list[SymbolInfo]] = {}
		self.import_graph: dict[str, set[str]] = {}

	def build(self, root_path: str) -> None:
		root = Path(root_path).resolve()
		self.root_path = root
		self.file_symbols = {}
		self.import_graph = {}

		py_files = sorted(root.rglob("*.py"))
		rel_paths = {self._to_rel_path(path): path for path in py_files}

		for rel_path, abs_path in rel_paths.items():
			source = abs_path.read_text(encoding="utf-8", errors="ignore")
			try:
				tree = ast.parse(source)
			except SyntaxError:
				# Brownfield indexing should be resilient to malformed files in the repo.
				continue

			symbols: list[SymbolInfo] = []
			imports: set[str] = set()

			for node in tree.body:
				if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
					symbols.append(SymbolInfo(name=node.name, docstring=ast.get_docstring(node)))
				elif isinstance(node, ast.Import):
					for alias in node.names:
						target = self._resolve_import_target(alias.name, rel_path, rel_paths)
						if target is not None:
							imports.add(target)
				elif isinstance(node, ast.ImportFrom):
					target = self._resolve_import_from(node, rel_path, rel_paths)
					if target is not None:
						imports.add(target)

			self.file_symbols[rel_path] = symbols
			self.import_graph[rel_path] = imports

	def find_impacted(self, keywords: list[str]) -> list[ImpactedArea]:
		if self.root_path is None:
			raise ValueError("Repo index has not been built yet")

		normalized = [kw.strip().lower() for kw in keywords if kw and kw.strip()]
		if not normalized:
			return []

		direct_matches: dict[str, list[str]] = {}

		content_matches = self._grep_keyword_matches(normalized)
		for rel_path, hit_keywords in content_matches.items():
			direct_matches.setdefault(rel_path, []).extend(hit_keywords)

		for rel_path, symbols in self.file_symbols.items():
			haystack_parts: list[str] = []
			for symbol in symbols:
				haystack_parts.append(symbol.name)
				if symbol.docstring:
					haystack_parts.append(symbol.docstring)
			haystack = "\n".join(haystack_parts).lower()
			if not haystack:
				continue
			matched = [kw for kw in normalized if kw in haystack]
			if matched:
				direct_matches.setdefault(rel_path, []).extend(matched)

		impacted_reasons: dict[str, str] = {}

		for rel_path, hit_keywords in direct_matches.items():
			unique_keywords = sorted(set(hit_keywords))
			reason = f"Matched keyword(s): {', '.join(unique_keywords)}"
			impacted_reasons[rel_path] = reason

		matched_files = set(direct_matches.keys())
		for importer, imported_files in self.import_graph.items():
			imported_hits = sorted(imported_file for imported_file in imported_files if imported_file in matched_files)
			if not imported_hits:
				continue
			importer_reason = f"Imports matched file: {', '.join(imported_hits)}"
			if importer in impacted_reasons:
				impacted_reasons[importer] = f"{impacted_reasons[importer]}; {importer_reason}"
				continue
			for imported_file in imported_files:
				if imported_file in matched_files:
					impacted_reasons[importer] = f"Imports matched file: {imported_file}"
					break

		impacted: list[ImpactedArea] = []
		for rel_path in sorted(impacted_reasons.keys()):
			impacted.append(
				ImpactedArea(
					module=self._module_name_from_rel_path(rel_path),
					files=[rel_path],
					reason=impacted_reasons[rel_path],
				)
			)
		return impacted

	def _grep_keyword_matches(self, keywords: list[str]) -> dict[str, list[str]]:
		assert self.root_path is not None
		pattern = "|".join(re.escape(keyword) for keyword in keywords)

		try:
			proc = subprocess.run(
				["rg", "-i", "-l", "--glob", "*.py", pattern, str(self.root_path)],
				check=False,
				capture_output=True,
				text=True,
			)
			# ripgrep exits with 1 when there are no matches.
			if proc.returncode in (0, 1):
				matches: dict[str, list[str]] = {}
				for line in proc.stdout.splitlines():
					path = Path(line.strip())
					if not path:
						continue
					rel_path = self._to_rel_path(path)
					content = path.read_text(encoding="utf-8", errors="ignore").lower()
					hit_keywords = [kw for kw in keywords if kw in content]
					if hit_keywords:
						matches[rel_path] = hit_keywords
				return matches
		except FileNotFoundError:
			pass

		return self._python_search_keyword_matches(keywords)

	def _python_search_keyword_matches(self, keywords: list[str]) -> dict[str, list[str]]:
		assert self.root_path is not None
		matches: dict[str, list[str]] = {}
		for path in self.root_path.rglob("*.py"):
			rel_path = self._to_rel_path(path)
			content = path.read_text(encoding="utf-8", errors="ignore").lower()
			hit_keywords = [kw for kw in keywords if kw in content]
			if hit_keywords:
				matches[rel_path] = hit_keywords
		return matches

	def _resolve_import_target(
		self,
		module_name: str,
		current_rel_path: str,
		rel_paths: dict[str, Path],
	) -> str | None:
		del current_rel_path
		candidates = self._candidates_for_module(module_name)
		for candidate in candidates:
			if candidate in rel_paths:
				return candidate
		return None

	def _resolve_import_from(
		self,
		node: ast.ImportFrom,
		current_rel_path: str,
		rel_paths: dict[str, Path],
	) -> str | None:
		module_name = node.module or ""
		current_module = self._module_name_from_rel_path(current_rel_path)
		current_parts = current_module.split(".") if current_module else []

		if node.level > 0:
			base_parts = current_parts[: max(0, len(current_parts) - node.level)]
			if module_name:
				base_parts.extend(module_name.split("."))
			resolved_module = ".".join(part for part in base_parts if part)
		else:
			resolved_module = module_name

		if resolved_module:
			for candidate in self._candidates_for_module(resolved_module):
				if candidate in rel_paths:
					return candidate

		for alias in node.names:
			if alias.name == "*":
				continue
			if resolved_module:
				maybe_module = f"{resolved_module}.{alias.name}"
			else:
				maybe_module = alias.name
			for candidate in self._candidates_for_module(maybe_module):
				if candidate in rel_paths:
					return candidate

		return None

	def _candidates_for_module(self, module_name: str) -> list[str]:
		dotted = module_name.strip(".")
		if not dotted:
			return []
		path_part = dotted.replace(".", "/")
		return [f"{path_part}.py", f"{path_part}/__init__.py"]

	def _to_rel_path(self, path: Path) -> str:
		assert self.root_path is not None
		return str(path.resolve().relative_to(self.root_path)).replace("\\", "/")

	def _module_name_from_rel_path(self, rel_path: str) -> str:
		module = rel_path.replace("/", ".")
		if module.endswith(".py"):
			module = module[:-3]
		if module.endswith(".__init__"):
			module = module[: -len(".__init__")]
		return module
