var MODEL_PARAM = {
    "DeepDaze": {
        "low": {
            "iter": 200,
            "num_layer": 24,
            "hidden_size": 256,
            "batch_size": 1,
            "gae": 1,
            "backbone": "RN50"
        },
        "middle": {
            "iter": 500,
            "num_layer": 24,
            "hidden_size": 512,
            "batch_size": 1,
            "gae": 1,
            "backbone": "RN50x4"
        },
        "high": {
            "iter": 1000,
            "num_layer": 24,
            "hidden_size": 512,
            "batch_size": 4,
            "gae": 1,
            "backbone": "ViT-B32"
        }
    },
    "BigSleep": {
        "low": {
            "iter": 60,
            "gae": 1,
            "backbone": "ViT-B32"
        },
        "middle": {
            "iter": 100,
            "gae": 1,
            "backbone": "RN50x4"
        },
        "high": {
            "iter": 150,
            "gae": 1,
            "backbone": "RN50"
        }
    }
}

