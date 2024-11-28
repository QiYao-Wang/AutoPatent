# datasets
mkdir -p datasets
mkdir -p datasets/LongForm
mkdir -p datasets/OpenHermes
# logs
mkdir -p logs
# outputs
mkdir -p outputs
mkdir -p outputs/checkpoints
mkdir -p outputs/multi_mlt
mkdir -p outputs/other_tasks
mkdir -p outputs/self_generated_mlt
mkdir -p outputs/tlg

# download longform
huggingface-cli download --repo-type dataset --resume-download akoksal/LongForm --local-dir ../datasets/LongForm
# download openhermes
huggingface-cli download --repo-type dataset --resume-download teknium/OpenHermes-2.5 --local-dir ../datasets/OpenHermes