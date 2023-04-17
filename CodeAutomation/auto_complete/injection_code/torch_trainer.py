#train_dist.py
import_expr = "from NetmindMixins.Netmind import nmp"

nmp_init_expr = "nmp.init()"

#finish_training_expr = "nmp.finish_training()"


trainer_import_expr = "from NetmindMixins.Netmind import nmp, NetmindTrainerCallback"

callback_expr = "class CustomTrainerCallback(NetmindTrainerCallback):"

trainer_expr = "callbacks=[CustomTrainerCallback]"
last_checkpoint_expr = "if args.do_train:"

load_checkpoint_expr =  "latest_checkpoint = nmp.last_checkpoint_from_netmind()"
    
train_expr =  "{}.train(resume_from_checkpoint=latest_checkpoint)"


# feature point
feature_optimizer = "optimizer = get_optimizer(model,args)"
feature_callback_class = "class CustomTrainerCallback(transformers.TrainerCallback)"
feature_callback_args = "callbacks=[CustomTrainerCallback]"
feature_train_function = "def train(tokenizer, data_collator, tokenized_datasets, model, optimizer, args)"


pytorch_trainer_visited_table = {
    nmp_init_expr: [False, feature_optimizer],
    callback_expr: [False, feature_callback_class],
    trainer_expr: [False, feature_callback_args],
    #last_checkpoint_expr: [False, ],
    load_checkpoint_expr: [False, feature_train_function],
    train_expr: [False, feature_train_function]
}