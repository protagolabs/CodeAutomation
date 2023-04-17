import_insert_line_expr = "from NetmindMixins.Netmind import  TensorflowTrainerCallback"
callback_insert_expr = "class CustomTrainerCallback(TensorflowTrainerCallback):"

fit_call_back_insert_expr = "netmind_callback = CustomTrainerCallback(batches_per_epoch=batches_per_epoch)"

all_back_expr = "callbacks = all_callbacks + [netmind_callback]"


#feature point to insert
feature_original_callback_expr = "class CustomTrainerCallback(tf.keras.callbacks.Callback):"
feature_mode_fit_expr = "model.fit"
feature_callback_agrs = "callbacks=all_callbacks"

#visited_table
tensorflow_trainer_visited_table = {
    callback_insert_expr: [False, feature_original_callback_expr],
    fit_call_back_insert_expr: [False, feature_mode_fit_expr],
    all_back_expr: [False, feature_callback_agrs],
}