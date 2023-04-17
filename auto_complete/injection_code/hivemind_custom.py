#optimizer.py
optimizer_htp_expr = "from NetmindMixins.Netmind import htp"
htp_init_expr = \
"""htp.init(
        {},
        {},
        {},
        collaboration_args.statistics_expiration
    )
"""

#run_trainer.py
run_trainer_htpimport_expr = "from NetmindMixins.Netmind import htp, NetmindModel"
htp_train_end = "htp.on_train_end()"


#run_training_monitor.py

training_monitor_import_expr = "from NetmindMixins.Netmind import  hmp, NetmindModel, NetmindOptimizer"

netmind_model_expr = "{} = NetmindModel({})"

hmp_save_pretrained_expr = "hmp.save_pretrained()"

hmp_init_expr = "hmp.init({}, {})"

hmp_step_expr = "hmp.step(current_step, monitor_metrics)"


optimizer_expr = "{} = NetmindOptimizer({})"
#trainer.py
trainer_import = "from NetmindMixins.Netmind import htp"

htp_set_batch_size_steps = \
"""if training_args.max_steps > 0:
        htp.set_max_steps(training_args.max_steps)
    else:
        htp.set_max_steps(math.ceil(training_args.num_train_epochs * num_update_steps_per_epoch))
    htp.set_total_train_batch_size(training_args.train_batch_size * training_args.gradient_accumulation_steps * training_args.world_size)
"""

htp_step_begin = "htp.on_step_begin()"

htp_step_end_if = "if htp.on_step_end(monitor_metrics):"
htp_step_end_comment = "# shutdown optimizer"
htp_step_end_inner_if = "if hasattr(optimizer, \"is_alive\") and optimizer.is_alive():"
htp_step_end_shut = "optimizer.shutdown()"
htp_step_end_exit = "sys.exit(0)"





#htp_log = "htp.log({\"top1\": top1.avg.item(), \"top5\": top5.avg.item()})"
