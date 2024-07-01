{
  description = "Use the solidpython2 flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    solidpython2 = {
      url = "github:jonboh/nix-environments?dir=solidpython2";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    solidpython2,
    ...
  } @ inputs: let
    system = "x86_64-linux";
    pkgs = import nixpkgs {
      inherit system;
    };
  in {
    devShells.${system}.default = pkgs.mkShell {
      packages = [
        pkgs.openscad-unstable # currently broken for ulp-dactyl models, use dev snapshots from April 2024
        pkgs.pyright
        (pkgs.python3.withPackages
          (ps:
            with ps; [
              ruff-lsp
              autopep8
              debugpy
              setuptools
              solidpython2.packages.${system}.python3Packages.solidpython2
              numpy
            ]))
      ];
    };
  };
}
