#!/bin/bash

export CUDA_VISIBLE_DEVICES=7

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialValidator \
    mosaic \
    python mosaic_subnet/cli.py agent.ArtificialValidator agent.ArtificialValidator "66.226.79.190" 50056

export CUDA_VISIBLE_DEVICES=7

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialGateway \
    mosaic \
    python mosaic_subnet/cli.py agent.ArtificialGateway agent.ArtificialGateway "66.226.79.190" 50050

export CUDA_VISIBLE_DEVICES=6

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialMiner \
    mosaic \
    python mosaic_subnet/cli.py miner agent.ArtificialMiner agent.ArtificialMiner "66.226.79.190" 50056

export CUDA_VISIBLE_DEVICES=1

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialMiner_1 \
    mosaic \
    python mosaic_subnet/cli.py miner agent.ArtificialMiner_1 agent.ArtificialMiner_1 "66.226.79.190" 50052

export CUDA_VISIBLE_DEVICES=2

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialMiner_2 \
    mosaic \
    python mosaic_subnet/cli.py miner agent.ArtificialMiner_2 agent.ArtificialMiner_2 "66.226.79.190" 50052

export CUDA_VISIBLE_DEVICES=3

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialMiner_3 \
    mosaic \
    python mosaic_subnet/cli.py miner agent.ArtificialMiner_3 agent.ArtificialMiner_3 "66.226.79.190" 50053

export CUDA_VISIBLE_DEVICES=4

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialMiner_4 \
    mosaic \
    python mosaic_subnet/cli.py miner agent.ArtificialMiner_4 agent.ArtificialMiner_4 "66.226.79.190" 50054

export CUDA_VISIBLE_DEVICES=5

docker run --gpus=all -d --network host --restart always \
    -v $HOME/.commune:/root/.commune \
    -v $HOME/.cache/huggingface:/root/.cache/huggingface \
    --name agent.ArtificialMiner_5 \
    mosaic \
    python mosaic_subnet/cli.py miner agent.ArtificialMiner_5 agent.ArtificialMiner_5 "66.226.79.190" 50055
