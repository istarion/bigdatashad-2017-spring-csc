## Семинар 6.
### Spark

Задача: пишем простые программы на Python для Spark.

#### Запуск консоли (с использованием ipython)

- В локальном режиме

        IPYTHON=1 pyspark --master local[4]
- В распределенном режиме на кластере:

        IPYTHON=1 pyspark --master yarn --num-executors 4

В обоих примерах - по 4 исполнителя (executor’а).

Доступен объект SparkContext:

    >>> type(sc)
    pyspark.context.SparkContext

Прочитаем лог в rdd:

    >>> log = sc.textFile('/user/sandello/logs/access.log.2016-10-07')
    >>> type(log)
    pyspark.rdd.RDD

Преобразуем строки лога, выделим ip-адреса и посчитаем уникальные:

    >>> ips = log.map(lambda x: x.strip().split()[0])
    >>> uniq_ips = ips.distinсt()

Все работает быстро, но и вычислений пока нет. Запускаем:

    >>> uniq_ips.count()
    9178

Операции над RDD: преобразования (RDD -> RDD); действия (RDD -> другой тип). Действия запускают вычисления.

Примеры преобразований: `map, filter, distinct`

Примеры действий: `reduce, count, collect, take, top`

Для преобразований запоминается, как и откуда получается новая RDD. Это можно посмотреть так:

    >>> print uniq_ips.toDebugString()

#### Работа с парами key-value
Создадим нужную RDD:

    >>> ips1 = ips.map(lambda x: (x, 1))
И посчитаем число вхождений каждого IP:

    >>> ips_count = ips1.reduceByKey(lambda x, y: x+y)
Отфильтруем часть IP:

    >>> ips_filtered = ips_count.filter(lambda x: x[1] > 50)

Запустим расчет:

    >>> ips_filtered.count()

Другое действие приведет опять к запуску расчета. Чтобы этого избежать, разместим RDD в памяти:

    >>> ips_filtered.persist()
После этого в выводе метода `toDebugString()` это будет видно:

    (2) PythonRDD[26] at RDD at PythonRDD.scala:43 [Memory Serialized 1x Replicated]
    |       CachedPartitions: 2; MemorySize: 365.0 B; ExternalBlockStoreSize: 0.0 B; DiskSize: 0.0 B

То, что RDD размещена в памяти можно проверить:
    >>> ips_filtered.is_cached

Получение подсказки в консоли (для объекта ips, например):

    >>> ips.foldByKey?
и списка методов:

    >>> dir(ips)

Отладка на малых данных - задаем их непосредственно в методе parallelize:

    >>> rdd = sc.parallelize([1, 3, 6])
    >>> rdd.fold(0, lambda x, y: x*y)
    18

#### Автономный скрипт
В начале скрипта инициализируем контекст:

    from pyspark import SparkConf, SparkContext
    conf = SparkConf().setAppName("User sessions")
    sc = SparkContext(conf=conf)
и далее действуем по аналогии с консолью.

Запуск скрипта - при помощи spark-submit:

    $ spark-submit --master yarn script.py

#### Веб-интерфейс
При запуске (как консоли, так и скрипта) появляется сообщение наподобие:

    ui.SparkUI: Started SparkUI at http://93.158.137.65:4042
Т.е. веб-интерфейс этого Spark-контекста будет открываться тут: `http://hadoop2.yandex.ru:4042`

#### Более сложный пример
Пример скрипта, реализующего secondary sort и подсчет сессий: `user_sessions.py`

В скрипте для группировки по первой части ключа и сортировки по второй используется `repartitionAndSortWithinPartitions()`. Эффект от repartition (т.е. перераспределения) можно увидеть, сравнив:

    >>> sc.parallelize([1, 3, 6]).repartition(3).glom().collect()
и

    >>> sc.parallelize([1, 3, 6]).repartition(2).glom().collect()
(запускать желательно с >=3 исполнителями).

#### Упражнения
1. В скрипт добавьте код, который просуммирует статистику по всем IP и сравните со своими результатами из hw1.

2. Есть ли другая реализация secondary sort на Spark+Python? Если есть, то опишите её (т.е. помимо ссылки на stackoverflow или вроде того нужны еще несколько фраз, описывающих механизм работы).

3. Выполните

        >>>  sc.parallelize([1, 3, 6]).fold(1, lambda x, y: x*(y+1))
и объясните результат.

#### Полезные ссылки
- Guide: [http://spark.apache.org/docs/latest/programming-guide.html](http://spark.apache.org/docs/latest/programming-guide.html)
- Reference: [http://spark.apache.org/docs/latest/api/python/pyspark.html](http://spark.apache.org/docs/latest/api/python/pyspark.html)


