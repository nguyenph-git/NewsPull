#!/usr/bin/env python3
"""
Test script to verify ZhipuAI API key and model access.

Run with: ./test-api
"""

import os
import sys
from pathlib import Path

# Add newspull to Python path if installed in development mode
project_root = Path(__file__).parent
if (project_root / "newspull").exists():
    src_path = project_root / "newspull"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

# Load environment variables from .env file
env_file = project_root / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

def test_model(model_name: str) -> bool:
    """Test if a specific model works"""
    import asyncio
    from zhipuai import ZhipuAI

    api_key = os.environ.get("ZHIPUAI_API_KEY")
    if not api_key:
        print("[red]✗[/red] ZHIPUAI_API_KEY not set in .env")
        return False

    print(f"\n[cyan]Testing model: [bold]{model_name}[/bold][/cyan]")
    client = ZhipuAI(api_key=api_key)

    try:
        response = asyncio.run(
            client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Say hello in exactly 5 words."}],
            )
        )
        result = response.choices[0].message.content
        print(f"[green]✓[/green] Success! Response: {result}")
        return True
    except Exception as e:
        error_msg = str(e)
        if hasattr(e, 'response') and hasattr(e.response, 'json'):
            try:
                error_data = e.response.json()
                if 'error' in error_data:
                    print(f"[red]✗[/red] API Error: {error_data['error']}")
                    return False
            except:
                pass
        print(f"[red]✗[/red] Error: {error_msg}")
        return False

def main():
    """Main test function"""
    print("[bold]Testing ZhipuAI API Access[/bold]")
    print("=" * 50)

    models_to_test = [
        "glm-4",
        "glm-4-flash",
        "glm-4-flashx",
    ]

    working_models = []
    for model in models_to_test:
        if test_model(model):
            working_models.append(model)
        print()

    print("\n" + "=" * 50)
    print("\n[bold]Summary:[/bold]")

    if working_models:
        print(f"[green]✓[/green] Working models: {', '.join(working_models)}")
        print("\n[dim]You can update digester.py to use any working model by changing:[/dim]")
        print("  model=\"MODEL_NAME\" on line ~35")
    else:
        print("[red]✗[/red] No models worked. Check:")
        print("  1. API key is valid")
        print("  2. Account has credits")
        print("  3. Visit: https://z.ai/console")

if __name__ == "__main__":
    main()
