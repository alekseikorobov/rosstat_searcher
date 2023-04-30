

class SystemStatus:
    NEW = 'new' #загружаем из txt
    #INPROCESSING = 'InProcessing' #в процессе обновления
    UPDATE = 'update' #статус для отправки на обновление
    SUCCESS = 'success' #успешно обновлено
    ERROR = 'error' #ошибка обновления
    NOFORMS = 'noforms' #форм не найдено 
    
    @staticmethod
    def get_values():
        k = SystemStatus.__dict__        
        k = [k[x] for x in k if x != 'get_values' and not x.startswith('__')]    
        return k


if __name__ == "__main__":    
    print(SystemStatus.get_values()) 