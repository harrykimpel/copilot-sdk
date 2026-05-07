import asyncio
import os

from copilot import CopilotClient, SubprocessConfig
from copilot.generated.session_events import (
    AssistantMessageData,
    AssistantReasoningData,
    ToolExecutionStartData,
)
from copilot.session import PermissionHandler

nr_license_key = os.environ["NEW_RELIC_LICENSE_KEY"]
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "https://otlp.nr-data.net:4318"
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"api-key={nr_license_key}"
os.environ["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/protobuf"
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "true"

BLUE = "\033[34m"
RESET = "\033[0m"


async def main():
    client = CopilotClient(SubprocessConfig(
        telemetry={"exporter_type": "otlp-http"},
    ))
    await client.start()
    session = await client.create_session(on_permission_request=PermissionHandler.approve_all)

    def on_event(event):
        output = None
        match event.data:
            case AssistantReasoningData() as data:
                output = f"[reasoning: {data.content}]"
            case ToolExecutionStartData() as data:
                output = f"[tool: {data.tool_name}]"
        if output:
            print(f"{BLUE}{output}{RESET}")

    session.on(on_event)

    print("Chat with Copilot (Ctrl+C to exit)\n")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        print()

        reply = await session.send_and_wait(user_input)
        assistant_output = None
        if reply:
            match reply.data:
                case AssistantMessageData() as data:
                    assistant_output = data.content
        print(f"\nAssistant: {assistant_output}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")
