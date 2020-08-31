with import <nixpkgs> {};
stdenv.mkDerivation {
  name = "feedmael";
  buildInputs = [ (python3.withPackages (ps: with ps; [ feedparser ])) curl ];
}
