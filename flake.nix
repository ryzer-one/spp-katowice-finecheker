{
  description = "SPP Katowice Finechecker dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python312;
        py = python.withPackages (ps: with ps; [
          pip setuptools wheel
          selenium paho-mqtt
          # tomli only needed for <3.11, included here for convenience
          tomli
          black ruff pytest
        ]);
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [ py pkgs.chromium pkgs.chromedriver ];
          shellHook = ''
            export PIP_DISABLE_PIP_VERSION_CHECK=1
            echo "Dev shell: python=$(python --version) chromium=$(chromium --version)"
          '';
        };
      }
    );
}

