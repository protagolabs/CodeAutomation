import os

compress_dict=[

        {"pytorch/language-modeling/local" : ("trainer_customer/", "local_torch/mlm_trainer_customer")},

        {"pytorch/language-modeling/local" : ("trainer_Huggince/", "local_torch/mlm_trainer_Huggince")},

        {"pytorch/resnet": ("local/", "local_torch/resnet")},

        {"tensorflow/local": ("language-modeling/" , "local_tf/language-modeling")},

        {"tensorflow/local": ("image-classification-custom/", "local_tf/image-classification-custom")},

        {"tensorflow/local": ("image-classification/", "local_tf/image-classification")},

        {"pytorch/language-modeling/netmind" : ("trainer_customer/", "netmind_torch/mlm_trainer_customer")},

        {"pytorch/language-modeling/netmind" : ("trainer_Huggince/", "netmind_torch/mlm_trainer_Huggince")},

        {"pytorch/resnet": ("netmind/", "netmind_torch/resnet")},

        {"tensorflow/netmind": ("language-modeling/" , "netmind_tf/language-modeling")},

        {"tensorflow/netmind": ("image-classification-custom/", "netmind_tf/image-classification-custom")},

        {"tensorflow/netmind": ("image-classification/", "netmind_tf/image-classification")}

]

src_base_dir = "/Users/yang.li/Desktop/project/Netmind-examples/"
dst_base_dir = "/Users/yang.li/Desktop/project/CodeAutomation/tests/accuracy_prompts/"
root_dir = os.getcwd()

final_status_list = []

if __name__ == '__main__':

    for info in compress_dict:
        for k,v in info.items():
            assert len(v) == 2
            src_dir = os.path.join(src_base_dir, k)
            src_dir = os.path.join(src_dir, v[0])
            dst_dir = os.path.join(dst_base_dir, v[1])
            command = f"cp -rf  {src_dir} {dst_dir}"
            print(f'execute command : {command}')

            ret = os.system(command)
            if ret != 0:
                print(f'command : {command} executed failed, ret : {ret}')
                final_status_list.append(command)
                continue
            print(f'command : {command} executed sucessfully, ret : {ret}')

    if len(final_status_list) > 0:
        print(f'execution failed {final_status_list}')