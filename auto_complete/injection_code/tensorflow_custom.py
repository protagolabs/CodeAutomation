
# insert code expession
import_expr = "from NetmindMixins.Netmind import nmp, NetmindDistributedModel"
nmp_init_expr = "nmp.init()"
model_distibuted_expr = "NetmindDistributedModel(model)"
init_train_bar_expr = "nmp.init_train_bar(total_epoch=args.num_train_epochs, step_per_epoch=train_num//global_batch_size)"
init_eval_bar_expr = "nmp.init_eval_bar(total_epoch=args.num_train_epochs)"
should_skip_expr = \
"""if nmp.should_skip_step():
                continue
"""


step_expr = "nmp.step(train_monitor_metrics)"
evaluate_expr = "nmp.evaluate(eval_monitor_metrics) "
finish_training_expr = "nmp.finish_training()"

#feature point to insert
feature_multi_worker_mirrored_strategy_expr = "mirrored_strategy = tf.distribute.MultiWorkerMirroredStrategy()"
feature_out_loop_expr = "for epoch in range(args.num_train_epochs):"
feature_inner_loop_expr = "for ds in tqdm(train_data_iterator):"
feature_main_function_expr = "if __name__ == '__main__':"

#visited_table
tensorflow_custom_visited_table = {
    nmp_init_expr: [False, feature_multi_worker_mirrored_strategy_expr],
    model_distibuted_expr: [False, feature_out_loop_expr],
    init_train_bar_expr: [False, feature_out_loop_expr],
    init_eval_bar_expr: [False, feature_out_loop_expr],
    should_skip_expr: [False, feature_inner_loop_expr],
    step_expr: [False, feature_inner_loop_expr],
    evaluate_expr: [False, feature_inner_loop_expr],
    finish_training_expr: [False, feature_main_function_expr]

}