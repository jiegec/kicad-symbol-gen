import enum
from typing import Optional
import yaml
import click
import sexpdata
from sexpdata import Symbol

unit = 2.54
half_unit = 2.54 / 2


def gen_property(
    key: str,
    value: str,
    id: int,
    x: float,
    y: float,
    hidden: bool,
    justify: Optional[str] = None,
):
    if hidden:
        hidden_sexp = [Symbol("hide")]
    else:
        hidden_sexp = []
    if justify:
        justify_sexp = [[Symbol("justify"), Symbol(justify)]]
    else:
        justify_sexp = []
    return [
        Symbol("property"),
        key,
        value,
        [Symbol("id"), id],
        [Symbol("at"), x, y, 0],
        [Symbol("effects"), [Symbol("font"), [Symbol("size"), half_unit, half_unit]]]
        + hidden_sexp
        + justify_sexp,
    ]


def gen_pin(input: bool, name: str, index: int, width: float, height: float):
    if input:
        direction = Symbol("input")
        x = -width / 2 - unit
        angle = 0
    else:
        direction = Symbol("output")
        x = width / 2 + unit
        angle = 180
    y = height / 2 - unit * (index + 1)
    return [
        Symbol("pin"),
        direction,
        Symbol("line"),
        [Symbol("at"), x, y, angle],
        [Symbol("length"), unit],
        [
            Symbol("name"),
            name,
            [
                Symbol("effects"),
                [Symbol("font"), [Symbol("size"), half_unit, half_unit]],
            ],
        ],
        [
            Symbol("number"),
            "",
            [
                Symbol("effects"),
                [Symbol("font"), [Symbol("size"), half_unit, half_unit]],
            ],
        ],
    ]


@click.command(help="Generate kicad symbol from module description")
@click.argument("config_yaml", type=click.Path(exists=True))
def work(
    config_yaml: str,
):
    config = yaml.load(open(config_yaml, "r"), yaml.SafeLoader)

    sexp = [Symbol("kicad_symbol_lib")]
    sexp.append([Symbol("version"), 20211014])
    sexp.append([Symbol("generator"), Symbol("kicad-symbol-gen")])

    for symbol in config:
        name = symbol["name"]
        inputs = symbol["inputs"]
        outputs = symbol["outputs"]

        if "sequential" in symbol:
            sequential = symbol["sequential"]
        else:
            sequential = False

        if sequential:
            output_len_additional = 2
        else:
            output_len_additional = 0

        height = (max(len(inputs), len(outputs) + output_len_additional) + 1) * unit
        width = symbol["width"] * unit

        symbol_sexp = [Symbol("symbol")]
        symbol_sexp.append(name)
        symbol_sexp.append([Symbol("in_bom"), Symbol("yes")])
        symbol_sexp.append([Symbol("on_board"), Symbol("yes")])
        symbol_sexp.append(
            gen_property(
                "Reference", "U", 0, -width / 2, height / 2 + unit / 2, False, "left"
            )
        )
        symbol_sexp.append(
            gen_property(
                "Value", name, 1, width / 2, height / 2 + unit / 2, False, "right"
            )
        )
        symbol_sexp.append(gen_property("Footprint", "", 2, 0, 0, True))
        symbol_sexp.append(gen_property("Datasheet", "", 3, 0, 0, True))

        if sequential:
            polyline_sexp = [
                [
                    Symbol("polyline"),
                    [
                        Symbol("pts"),
                        [Symbol("xy"), width / 2 - 3 * unit, -height / 2],
                        [Symbol("xy"), width / 2 - 2 * unit, -height / 2 + 2 * unit],
                        [Symbol("xy"), width / 2 - 1 * unit, -height / 2],
                    ],
                    [
                        Symbol("stroke"),
                        [Symbol("width"), 0],
                        [Symbol("type"), Symbol("default")],
                        [Symbol("color"), 0, 0, 0, 0],
                    ],
                    [Symbol("fill"), [Symbol("type"), Symbol("none")]],
                ]
            ]
        else:
            polyline_sexp = []

        symbol_sexp.append(
            [
                Symbol("symbol"),
                f"{name}_0_1",
                [
                    Symbol("rectangle"),
                    [Symbol("start"), -width / 2, height / 2],
                    [Symbol("end"), width / 2, -height / 2],
                    [
                        Symbol("stroke"),
                        [Symbol("width"), 0],
                        [Symbol("type"), Symbol("default")],
                        [Symbol("color"), 0, 0, 0, 0],
                    ],
                    [Symbol("fill"), [Symbol("type"), Symbol("none")]],
                ],
            ]
            + polyline_sexp
        )

        pin_sexp = []
        for index, pin in enumerate(inputs):
            pin_sexp.append(gen_pin(True, pin, index, width, height))
        for index, pin in enumerate(outputs):
            pin_sexp.append(gen_pin(False, pin, index, width, height))

        symbol_sexp.append([Symbol("symbol"), f"{name}_1_1"] + pin_sexp)

        sexp.append(symbol_sexp)

    print(sexpdata.dumps(sexp))


if __name__ == "__main__":
    work()
