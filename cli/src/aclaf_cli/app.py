from aclaf import App

app = App()


@app.command()
def info() -> str:
    return "Hello from Aclaf CLI!"
