import os
import sys
from dotenv import load_dotenv
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import time

# Load environment variables
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Simplified style for the prompt
custom_style = Style.from_dict(
    {
        "prompt": "fg:cyan bold",
        "input": "fg:green",
    }
)


async def main():
    # Initialize console
    console = Console()

    # Print welcome message
    console.print(
        Panel.fit(
            "[bold cyan]Terminal AI Assistant[/bold cyan]\n"
            "[italic]Type your query or 'exit' to quit[/italic]",
            title="Welcome",
            border_style="blue",
        )
    )

    # Initialize Gemini/OpenAI-compatible provider
    provider = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    # Set up model and agent
    model = OpenAIChatCompletionsModel(
        model="gemini-2.5-flash",
        openai_client=provider,
    )

    agent = Agent(
        name="Terminal AI",
        instructions="""
        You are a helpful, general-purpose AI assistant designed to answer all types of user queries,
        including programming, writing, troubleshooting, and general knowledge.
        Since you operate in a command-line interface, avoid using markdown styling such as asterisks (*),
        hashes (#), or other formatting symbols that may not display well in terminal environments.
        Always respond in clear, plain text that is easy to read and understand in a terminal window.
        """,
        model=model,
    )

    # Initialize prompt session
    session = PromptSession(
        message=[
            ("class:prompt", "You: "),
        ],
        style=custom_style,
    )

    while True:
        try:
            # Get user input with nice prompt
            user_input = await session.prompt_async()

            if user_input.lower() in ("exit", "quit"):
                console.print("[italic]Goodbye![/italic]", style="yellow")
                break

            if not user_input.strip():
                continue

            # Show thinking indicator
            with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                # Run the agent with streaming output
                result = Runner.run_streamed(agent, input=user_input)

                # Print response header
                console.print(
                    Panel.fit(
                        "",
                        title="AI Response",
                        border_style="green",
                        subtitle=f"Model: gemini-2.5-flash",
                    )
                )

                full_response = ""
                start_time = time.time()

                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(
                        event.data, ResponseTextDeltaEvent
                    ):
                        delta = event.data.delta
                        full_response += delta
                        # Use Rich's Text for better control
                        text = Text(delta, style="yellow")
                        console.print(text, end="", highlight=False)

                # Add newline after response
                console.print()

                # Print performance info
                elapsed = time.time() - start_time
                console.print(
                    f"[dim]Response generated in {elapsed:.2f} seconds[/dim]",
                    style="blue",
                )

        except KeyboardInterrupt:
            console.print(
                "\n[italic]Press 'exit' to quit or continue your query...[/italic]",
                style="yellow",
            )
            continue
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            continue


if __name__ == "__main__":
    asyncio.run(main())
