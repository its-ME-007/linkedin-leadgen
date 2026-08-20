import os

from dotenv import load_dotenv
from google import genai


def main():

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    print("==============================")
    print("AVAILABLE GEMINI MODELS")
    print("==============================")

    client = genai.Client(
        api_key=api_key
    )

    try:

        models = client.models.list()

        count = 0

        for model in models:

            name = getattr(
                model,
                "name",
                None
            )

            supported_actions = getattr(
                model,
                "supported_actions",
                None
            )

            if not name:
                continue

            # We only care about models that can
            # perform generateContent.
            if (
                supported_actions
                and "generateContent"
                not in supported_actions
            ):
                continue

            print(
                f"\nModel: {name}"
            )

            if supported_actions:
                print(
                    f"Supported actions: "
                    f"{supported_actions}"
                )

            count += 1

        print(
            f"\n=============================="
        )

        print(
            f"Callable generation models: "
            f"{count}"
        )

        print(
            "=============================="
        )

    finally:

        client.close()


if __name__ == "__main__":
    main()