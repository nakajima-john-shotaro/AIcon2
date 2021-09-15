var MODEL_PARAM = {
    DeepDaze: {
        low: {
            iter: 400,
            num_layer: 24,
            hidden_size: 256,
            batch_size: 1,
            gae: 1,
            backbone: 'RN101'
        },
        middle: {
            iter: 800,
            num_layer: 24,
            hidden_size: 512,
            batch_size: 2,
            gae: 1,
            backbone: 'ViT-B32'
        },
        high: {
            iter: 1000,
            num_layer: 24,
            hidden_size: 1024,
            batch_size: 4,
            gae: 1,
            backbone: 'ViT-B32'
        },
    },
    BigSleep: {
        low: {
            iter: 100,
            gae: 1,
            backbone: 'RN50x4'
        },
        middle: {
            iter: 250,
            gae: 1,
            backbone: 'ViT-B32'
        },
        high: {
            iter: 400,
            gae: 1,
            backbone: 'ViT-B32'
        },
    }
}