import time

import click


@click.group()
def cli():
    pass


@cli.command()
def init():
    click.echo('Initialized the database')


@cli.command()
def tui():
    import pytermgui as ptg

    def macro_time(fmt: str) -> str:
        return time.strftime(fmt)

    ptg.tim.define("!time", macro_time)

    with ptg.WindowManager() as manager:
        layout = manager.layout
        layout.add_slot("Header", height=5)
        layout.add_slot("Header Left", width=0.2)

        layout.add_break()

        layout.add_slot("Body Left", width=0.2)
        layout.add_slot("Body", width=0.7)
        layout.add_slot("Body Right")

        layout.add_break()

        layout.add_slot("Footer", height=3)


if __name__ == '__main__':
    cli()
