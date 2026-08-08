from backend.generation.models import (
    GenerationContext,
    SourceReference,
)
from backend.generation.providers.ollama_generator import (
    OllamaGenerator,
)


context = GenerationContext(
    query="What does a Kubernetes Deployment manage?",
    context_text=(
        "[SOURCE 1]\n"
        "title: Kubernetes Documentation\n"
        "source: kubernetes\n"
        "document_id: doc-1\n"
        "chunk_id: chunk-1\n\n"
        "A Kubernetes Deployment manages "
        "a set of replicated application Pods."
    ),
    sources=[
        SourceReference(
            citation_id="1",
            document_id="doc-1",
            chunk_id="chunk-1",
            title="Kubernetes Documentation",
            source="kubernetes",
        )
    ],
    token_count=40,
)

generator = OllamaGenerator(
    model="qwen3:4b-instruct",
)

result = generator.generate(context)

print()
print("ANSWER")
print("------")
print(result.answer)

print()
print("CITATIONS")
print("---------")
print(result.citations)

print()
print("MODEL")
print("-----")
print(result.model)

print()
print("TOKENS")
print("------")
print("Prompt:", result.prompt_tokens)
print("Completion:", result.completion_tokens)
print("Total:", result.total_tokens)

print()
print("LATENCY")
print("-------")
print(f"{result.latency_ms:.2f} ms")