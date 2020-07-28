#!/usr/bin/env python3

from subprocess import run, PIPE
from typing import List
import click


LAPTOP_DISPLAY = "LVDS-1"


def connected_displays() -> List[str]:
    """Returns a list of the names of all connected displays
    """
    p = run(["xrandr"], stdout=PIPE, universal_newlines=True)
    stdout = p.stdout.splitlines()

    connected = [x for x in stdout if " connected" in x]
    connected = [x.split(" ")[0] for x in connected]

    return connected


@click.group()
def main():
    connected = connected_displays()


@main.command()
@click.option(
    "--left/-l", is_flag=True, help="Add new display to the left of the current display"
)
@click.option(
    "--dont-move-workspaces/-k",
    is_flag=True,
    help="Keep all workspaces on their current displays",
)
@click.option(
    "--high-res", is_flag=True, help="New display is 4k",
)
def add(left, dont_move_workspaces, high_res):
    """Add a new display to the right of laptop screen,
    or left with -l
    """
    connected = [x for x in connected_displays() if x != LAPTOP_DISPLAY]
    if not connected:
        print("No displays other than the laptop display")
        return

    if high_res:
        xrandr_mode = ["--mode", "2560x1440"]
    else:
        xrandr_mode = ["--auto"]

    # Temporarily shut off laptop display to move
    # all workspaces to external monitor
    if not dont_move_workspaces:
        run(
            [
                "xrandr",
                "--output",
                LAPTOP_DISPLAY,
                "--off",
                "--output",
                connected[0],
                "--primary",
            ]
            + xrandr_mode
        )

    position = "left" if left else "right"

    run(
        [
            "xrandr",
            "--output",
            LAPTOP_DISPLAY,
            "--primary",
            "--auto",
            "--output",
            connected[0],
            f"--{position}-of",
            LAPTOP_DISPLAY,
        ]
        + xrandr_mode
    )


@main.command()
def disconnect() -> None:
    """Disable all external displays and only use laptop screen
    """
    connected = [x for x in connected_displays() if x != LAPTOP_DISPLAY]
    for display in connected:
        run(
            ["xrandr", "--output", display, "--off",]
        )


@main.group()
def b():
    """Brightness control """
    pass


def change_brightness(new_brightness_fn) -> None:
    connected = [x for x in connected_displays() if x != LAPTOP_DISPLAY]
    if not connected:
        print("No displays other than the laptop display")
        return

    for display in connected:
        output = run(
            ["xrandr", "--verbose"], stdout=PIPE, universal_newlines=True
        ).stdout

        # Get current display brightness
        idx = output.find(display)
        idx = output.find("Brightness:", idx)
        output = output[idx:]
        _, brightness = output.splitlines()[0].split(" ")
        brightness = float(brightness)

        new_brightness = new_brightness_fn(brightness)

        run(
            ["xrandr", "--output", display, "--brightness", str(new_brightness),]
        )


@b.command()
def down():
    """Lower brightness
    """

    def f(brightness):
        new_brightness = brightness - 0.1
        if new_brightness < 0:
            new_brightness = 0

        return new_brightness

    change_brightness(f)


@b.command()
def up():
    """Increase brightness
    """

    def f(brightness):
        new_brightness = brightness + 0.1
        if new_brightness > 1:
            new_brightness = 1.0

        return new_brightness

    change_brightness(f)


@b.command()
def max():
    """Increase brightness to the maximum level
    """

    change_brightness(lambda _: 1.0)


main.add_command(add)


if __name__ == "__main__":
    main()
