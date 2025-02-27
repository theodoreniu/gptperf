import click


@click.command()
@click.option("--name", default="World", help="Name to greet.")
def main(name):
    click.echo(f"Hello, {name}! This is llmperf.")


if __name__ == "__main__":
    main()
