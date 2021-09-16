var MODEL_PARAM = {
    DeepDaze: {
        low: {
            iter: 200,
            num_layer: 12,
            hidden_size: 256,
            batch_size: 6,
            gae: 2,
            backbone: 'ViT-B32'
        },
        middle: {
            iter: 300,
            num_layer: 16,
            hidden_size: 256,
            batch_size: 12,
            gae: 4,
            backbone: 'ViT-B32'
        },
        high: {
            iter: 500,
            num_layer: 24,
            hidden_size: 512,
            batch_size: 24,
            gae: 4,
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