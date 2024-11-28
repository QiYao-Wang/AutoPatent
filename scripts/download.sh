# datasets
mkdir -p datasets

# outputs
mkdir -p outputs

# download D2P benchmark test set
huggingface-cli download --repo-type dataset --resume-download QiYao-Wang/D2P D2P-Benchmark/test.json --local-dir ../datasets