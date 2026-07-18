"""Entrypoint Streamlit dell’Atlante geografico per concorsi pubblici."""

from atlas import create_application


if __name__ == "__main__":
    create_application().run()
