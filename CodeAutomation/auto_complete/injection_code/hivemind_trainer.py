#callback.py
callback_import = "from NetmindMixins.Netmind import HivemindTrainerCallback"
class_expr = "class CollaborativeCallback(HivemindTrainerCallback):"
init_expr = "super().__init__(dht, optimizer, local_public_key, statistics_expiration)"

#train_begin_return_expr = "return super().on_train_begin(args, state, control, **kwargs)"
#step_end_return_expr = "return super().on_step_end(args, state, control, **kwargs)"



#run_training_monitor.py

training_monitor_import_expr = "from NetmindMixins.Netmind import hmp, NetmindModel, NetmindOptimizer"


netmind_model_expr = "{} = NetmindModel({})"

hmp_save_pretrained_expr = "hmp.save_pretrained()"

hmp_init_expr = "hmp.init(dht, local_public_key)"

hmp_step_expr = "hmp.step(current_step, monitor_metrics)"

optimizer_expr = "{} = NetmindOptimizer({})"
"""opt = NetmindOptimizer(
            Lamb(
                optimizer_grouped_parameters,
                lr=training_args.learning_rate,
                betas=(training_args.adam_beta1, training_args.adam_beta2),
                eps=training_args.adam_epsilon,
                weight_decay=training_args.weight_decay,
                clamp_value=training_args.clamp_value,
                debias=True,
            )
        )
"""

