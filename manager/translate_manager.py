from googletrans import Translator
import sys
import time

def translator(logger, src, dst, trans_str):
    result_str = ""
    is_translated = False
    error_cnt = 0
    while(not is_translated):
        if error_cnt > 5:
            logger.log_error(f"Failed to translate product description and shutdown the program")
            sys.exit()
        try:
            translator = Translator()
            result_str = translator.translate(text=trans_str, src=src, dest=dst).text
            time.sleep(2)
            is_translated = True
        except Exception as e:
            error_cnt += 1
            logger.log_error(f"Failed to translate product description : {e}")
    return result_str