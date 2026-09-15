from __future__ import annotations

import argparse
import json

from polynomial_dispersion_compiler import PolynomialDispersionCompiler


def numbers(text: str):
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Compile a discrete target mode from an even polynomial dispersion law."
    )
    parser.add_argument("--coefficients", required=True, help="c0,c1,... for g(k)=sum cp*k^(2p)")
    parser.add_argument("--target", required=True, type=int)
    parser.add_argument("--modes", required=True, help="comma-separated positive mode IDs")
    parser.add_argument("--q-bounds", required=True, help="positive lower,upper for q=(boundary_factor/L)^2")
    parser.add_argument("--boundary-factor", type=float, default=6.283185307179586)
    parser.add_argument("--lower", help="optional coefficient lower bounds")
    parser.add_argument("--upper", help="optional coefficient upper bounds")
    parser.add_argument("--observed-target-rate", type=float)
    parser.add_argument("--observed-rival-rate", type=float)
    args = parser.parse_args()

    coefficients = numbers(args.coefficients)
    modes = [int(v) for v in numbers(args.modes)]
    q_bounds = numbers(args.q_bounds)
    if len(q_bounds) != 2:
        parser.error("--q-bounds requires lower,upper")
    compiler = PolynomialDispersionCompiler(coefficients, args.boundary_factor)
    output = {"point_design": compiler.design(args.target, modes, q_bounds).__dict__}

    if bool(args.lower) != bool(args.upper):
        parser.error("--lower and --upper must be supplied together")
    if args.lower:
        lower, upper = numbers(args.lower), numbers(args.upper)
        output["fixed_quench_interval_design"] = compiler.design_interval(
            args.target, modes, q_bounds, lower, upper
        ).__dict__
        output["shape_interval_design"] = compiler.design_shape_interval(
            args.target, modes, q_bounds, lower, upper
        ).__dict__

    if (args.observed_target_rate is None) != (args.observed_rival_rate is None):
        parser.error("both observed rates are required for micro-probe calibration")
    if args.observed_target_rate is not None:
        output["microprobe_additive_quench"] = compiler.microprobe_quench(
            args.observed_target_rate, args.observed_rival_rate
        )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
