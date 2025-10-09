import os
import anthropic
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python claude_review.py <results.xml>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        logs = f.read()

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    print("Sending logs to Claude for analysis...")

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        temperature=1,
        system="You are the top analytical and provide solutions about DevOps from Top 500 fortune companies.",
        messages=[
            {"role": "user", "content": f"Analyze the following pytest report and summarize the results:\n\n{logs}"}
        ],
    )

    print("\n=== Claude Review Feedback ===\n")
    print(response.content[0].text)

if __name__ == "__main__":
    main()
