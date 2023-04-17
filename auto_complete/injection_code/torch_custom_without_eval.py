#train_dist.py
import_expr = "from NetmindMixins.Netmind import nmp, NetmindDistributedModel, NetmindOptimizer, NetmindDistributedModel"
nmp_init_expr = "nmp.init()"
model_distibuted_expr = \
"""ddp_model = NetmindDistributedModel(
        torch.nn.parallel.DistributedDataParallel({}, device_ids=[args.local_rank], output_device=args.local_rank)
    )
"""
optimizer_init_train_expr = \
"""{} = NetmindOptimizer(get_optimizer(ddp_model,args))
    nmp.init_train_bar(total_epoch=args.num_train_epochs, step_per_epoch=len({}))
"""
finish_training_expr = "nmp.finish_training()"


#trainer.py
nmp_import_expr = "from NetmindMixins.Netmind import nmp"
cur_epoch_expr = "{} = nmp.cur_epoch"
outer_loop_expr = "for {} in range({}, args.num_train_epochs):"
should_skip_expr = \
"""if nmp.should_skip_step():
                continue
"""

#step_expr = "nmp.step({\"loss\": loss.item(), \"Learning rate\": scheduler.get_last_lr()[0]})"
step_expr = "nmp.step(monitor_metrics)"
#save_pretrained_expr = "nmp.save_pretrained_by_step(args.save_steps)"


#feature point to insert
feature_data_sampler = "DistributedSampler(dataset)"
feature_distributed_model = "torch.nn.parallel.DistributedDataParallel"
feature_get_optimizer = "optimizer = get_optimizer(ddp_model,args)"
feature_main = "if __name__ == '__main__':"
feature_outloop = "for epoch in range(args.num_train_epochs):"
feature_innerloop = "for batch in dataloader:"



pytorch_mlm_custom_visited_table = {
    nmp_init_expr: [False, feature_data_sampler],
    model_distibuted_expr: [False, feature_distributed_model],
    optimizer_init_train_expr: [False, feature_get_optimizer],
    finish_training_expr: [False, feature_main],
    cur_epoch_expr: [False, feature_outloop],
    outer_loop_expr: [False, feature_outloop],
    should_skip_expr:  [False, feature_innerloop],
    step_expr:  [False, feature_innerloop],
}

