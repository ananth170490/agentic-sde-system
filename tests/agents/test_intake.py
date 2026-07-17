from orchestrator.agents.intake import IntakeAgent
from orchestrator.tools.model_provider import FakeModelProvider


MANDATORY_REQUIREMENT = "Build a scalable URL shortener service with APIs, persistence, and analytics."


def test_intake_agent_greenfield_url_shortener() -> None:
    fake_model = FakeModelProvider(
        canned_response={
            "raw_text": MANDATORY_REQUIREMENT,
            "category": "greenfield",
            "explicit_requirements": [
                "Build a scalable URL shortener service",
                "Include APIs",
                "Include persistence",
                "Include analytics",
            ],
            "implicit_requirements": [
                "Consider horizontal scaling for traffic growth",
                "Use load-balancing and stateless API nodes",
                "Design for high availability and monitoring",
            ],
            "ambiguities": [
                "Expected request throughput and latency SLOs are unspecified",
                "Authentication and authorization requirements for APIs are unspecified",
                "Analytics metric definitions and retention are unspecified",
            ],
            "ambiguity_score": 0.38,
        }
    )

    agent = IntakeAgent()
    spec = agent.run(MANDATORY_REQUIREMENT, fake_model)

    assert spec.category == "greenfield"
    assert spec.ambiguity_score is not None
