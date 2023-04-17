# train_dist.py
import_expr = "from NetmindMixins.Netmind import nmp, NetmindDistributedModel, NetmindOptimizer"
nmp_init_expr = "nmp.init()"
model_distibuted_expr = \
"""ddp_model = NetmindDistributedModel(
        torch.nn.parallel.DistributedDataParallel({}, device_ids=[args.local_rank], output_device=args.local_rank)
    )
"""


optimizer_expr = "{} = NetmindOptimizer(get_optimizer(ddp_model,args))"


init_train_bar_expr = "nmp.init_train_bar(total_epoch=args.num_train_epochs, step_per_epoch=len({}))"
init_eval_bar_expr = "nmp.init_eval_bar(total_epoch=args.num_train_epochs)"

finish_training_expr = \
"""    nmp.finish_training()
"""

# trainer.py
nmp_import_expr = "from NetmindMixins.Netmind import nmp"
cur_epoch_expr = "{} = nmp.cur_epoch"
outer_loop_expr = "for {} in range({}, args.num_train_epochs):"


should_skip_expr = "if nmp.should_skip_step():"
continue_expr = "continue"

step_expr = "nmp.step(monitor_metrics)"
evaluate_expr = "nmp.evaluate(monitor_metrics)"
#save_pretrained_expr = "nmp.save_pretrained(extra_dir_or_files=filename)"



#feature point to insert
feature_data_sampler = "train_sampler = DistributedSampler(train_dataset)"
feature_distributed_model = "torch.nn.parallel.DistributedDataParallel"
feature_get_optimizer = "optimizer = get_optimizer(model,args)"
feature_main = "if __name__ == '__main__':"

feature_outloop = "for epoch in range(int(args.num_train_epochs)):"
feature_innerloop = "for i, (images, target) in enumerate(train_loader):"
feature_validate = "def validate(val_loader, model, criterion, args, device):"


pytorch_resnet_custom_visited_table = {
    nmp_init_expr: [False, feature_data_sampler],
    model_distibuted_expr: [False, feature_distributed_model],
    optimizer_expr: [False, feature_get_optimizer],
    init_train_bar_expr: [False, feature_get_optimizer],
    init_eval_bar_expr: [False, feature_get_optimizer],
    finish_training_expr: [False, feature_main],

    cur_epoch_expr: [False, feature_outloop],
    outer_loop_expr: [False, feature_outloop],
    should_skip_expr:  [False, feature_innerloop],
    continue_expr:  [False, feature_innerloop],
    step_expr:  [False, feature_innerloop],
    evaluate_expr:  [False, feature_validate]
}