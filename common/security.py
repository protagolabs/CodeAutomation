def contain_miner_code(content: str):
    if content.find("stratum+") != -1:
        return True
    return False
