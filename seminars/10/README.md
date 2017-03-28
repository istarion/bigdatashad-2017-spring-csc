## Семинар 10.
### Hive

На семинаре будет рассмотрено:
- создание и заполнение таблиц Hive
- простые запросы
- подзапросы и join таблиц
- оконные функции SQL.

После семинара студент должен суметь:
- решить домашнее задание hw4

### Материалы семинара

Запускаем Hive-клиент:

    $ hive
Список имеющихся баз данных:

    hive> SHOW DATABASES;
Создаем свою и делаем ее текущей:

    hive> CREATE DATABASE agorokhov;
    hive> USE agorokhov;
Список таблиц пока пуст и это правильно:

    hive> SHOW TABLES;

#### Создание таблицы с логами
Будем создавать таблицы, тут потребуется какая-нибудь документация, например: [https://cwiki.apache.org/confluence/display/Hive/Home](https://cwiki.apache.org/confluence/display/Hive/Home)

Вот таблица для логов:

    hive> CREATE EXTERNAL TABLE access_log (
        ip STRING,
        date STRING,
        url STRING,
        status STRING,
        referer STRING,
        user_agent STRING
    )
    PARTITIONED BY (day string)
    ROW FORMAT SERDE 'org.apache.hadoop.hive.contrib.serde2.RegexSerDe'
    WITH SERDEPROPERTIES (
        "input.regex" = "([\\d\\.:]+) - - \\[(\\S+) [^\"]+\\] \"\\w+ ([^\"]+) HTTP/[\\d\\.]+\" (\\d+) \\d+ \"([^\"]+)\" \"(.*?)\""
    )
    STORED AS TEXTFILE;

Тут написано, то эта таблица:
- внешняя (external), т.е. только метаданные над данными в HDFS
- разбита на партиции.

Если все поля получаются NULL, это значит, что `input.regex` неправильный, т.е. он не разбирает строку. При этом есть нюанс: он должен соответствовать строке целиком, как будто в конце стоит `$`. Поэтому всегда полезно проверять, сколько NULL в вашей таблице (или партиции).

Партиции позволяют ограничить данные, с которыми будем работать.

Подробности про таблицу:

    hive> DESCRIBE access_log;
или

    hive> DESCRIBE EXTENDED access_log;

Добавляем партиции:

    hive> ALTER TABLE access_log ADD PARTITION(day='2016-12-01')
    LOCATION '/user/agorokhov/logs/2016-12-01';
Список партиций:

    hive> SHOW PARTITIONS access_log;
    OK
    day=2016-12-01

**Задание 1.**
Создайте database с именем своего логина, в ней - партицированную таблицу с логами. При этом LOCATION может (даже стоит) указывать на директории в `/user/bigdatashad/logs/`. Сделайте свой сэмпл лога, положите в отдельную директорию и подключите как отдельную партицию - для отладки. (Кстати, в day не обязательно должна быть дата, может быть и любая строка).

#### Managed таблицы
Если создавать таблицы без слова EXTERNAL, то ею будет полностью управлять Hive. И при удалении таблицы будут стерты данные в HDFS (для external таблиц это не так).
Плюс таких таблиц - можно использовать типы данных и более эффективные форматы.

    CREATE TABLE parsed_text_log (
        ip STRING,
        date TIMESTAMP,
        status SMALLINT,
        url STRING,
        referer STRING
    )
    STORED AS TEXTFILE;
Пример заполнения таблицы:

    INSERT OVERWRITE TABLE parsed_text_log
    SELECT
        ip,
        from_unixtime(unix_timestamp(date ,'dd/MMM/yyyy:HH:mm:ss')),
        CAST(status AS smallint),
        url,
        referer
    FROM access_log
    WHERE day='2015-11-18';

Данные таблицы хранятся по умолчанию в директории на кластере `/user/hive/warehouse/<DATABASE>/<TABLE>`. Текстовый файл можно читать самому, без hive, например, эту таблицу:

    $ hadoop fs -cat /user/hive/warehouse/<YOUR_DB_NAME>.db/parsed_text_log/000000_0 | head
(если вы выполнили задание 1, то имя вышей базы совпадает с логином).

При создании таблицы можно указать более привычные разделители полей с помощью ROW FORMAT. Можно указать более эффективный формат, например STORED AS RCFILE.

#### Запросы
Далее можно делать запросы:

    hive> SELECT * FROM access_log WHERE day='2015-11-16' LIMIT 1;
    OK
    62.56.137.239   16/Nov/2015:00:00:00    GET     /megabook/admin.cgi     HTTP/1.1        2015-11-16

Чуть более “сложный” запрос:

    hive> SELECT ip FROM access_log WHERE day='2015-11-16' LIMIT 10;
запрос упадет с ошибкой, потому что нужны классы из hive-contrib.jar, их нужно подключить так:

    hive> ADD JAR /opt/cloudera/parcels/CDH-5.9.0-1.cdh5.9.0.p0.23/lib/hive/lib/hive-contrib.jar;
Т.е. практически всегда в начале сеанса работы с Hive надо делать этот ADD JAR.

Еще более сложный пример: посчитаем число уникальных посетителей и хитов в логе за день (как в hw1). Кстати, запросы удобно писать в отдельном файле, а в hive передавать через ключ -f:

    $ hive -f query.hql

Итак, решение:

    SELECT count(distinct ip), count(1)
    FROM access_log
    WHERE day='2015-11-18' AND status='200';

То же, но для каждого url в отдельности лучше не выводить на экран, а сохранить в таблицу, например так:

    CREATE TABLE urls_stat
    STORED AS TEXTFILE
    AS
    SELECT url, count(distinct ip) AS users, count(1) AS hits
    FROM access_log
    WHERE day='2015-11-18' AND status='200'
    GROUP BY url
    ORDER BY hits DESC;
Далее можно делать запросы на стандартном SQL с использованием множества функций, стандартных и характерных для Hive.

**Задание 2.**
Посчитайте аналогичную статистику, но не по url, а по доменам. Для выделения домена можно использовать функцию Hive split().

#### Подзапросы
Подзапросы в Hive тоже есть. Понадобятся для задания 2 (выше) и в HW4.

    SELECT ... FROM (subquery) alias
    SELECT ... FROM table WHERE field IN (subquery)
В документации часто встречаются ограничения на версию hive, ее полезно знать:

    $ hive --version

**Задание 3.**
Напишите запрос, выводящий все запросы, пришедшие с 10 самых активных IP. Для этого используем форму подзапроса `WHERE ... IN (subquery)`, в подзапросе будет выбор нужных IP. Чуть более сложный вариант: статистика по url для этих IP.

#### Join таблиц
В Hive есть join таблиц с рядом оговорок, следующих из идеи MapReduce, например, условие может быть только на равенство. Синтаксис обычен для SQL:

    SELECT ... FROM a JOIN b ON (a.id = b.id)
Вместо таблиц можно использовать подзапросы. Есть Hive специфика, так, можно указать, что надо использовать идею map-side join:

    SELECT /*+ MAPJOIN(b) */ ... FROM a JOIN b ON a.id = b.id
если таблица b небольшая.

#### Оконные и аналитические функции
Допустим, надо построить рейтинг популярных страниц за день. Т.е. в таблицу urls_stat добавить номер строки. Для этого есть конструкция `func OVER w`, где w задает набор записей, к которому будет применена func.

Поэтому запрос:

    SELECT url, hits, row_number() OVER () FROM urls_stat LIMIT 10;
пронумерует строки в таблице, но это не будет рейтингом, т.к. не указана сортировка.

То же, но уже с сортировкой:

    SELECT url, hits, row_number() OVER (ORDER BY hits DESC) FROM urls_stat LIMIT 10;

Теперь усложним задачу: запрос будет по нескольким дням, а рейтинг нужно строить отдельный для каждого дня (представим, что в urls_stat поле day есть). Для этого в  запрос добавляется PARTITION BY:

    SELECT day, url, hits, row_number() OVER (PARTITION BY day ORDER BY hits DESC) FROM urls_stat;
При создании таблиц у нас уже были партиции, так вот, это совсем другие партиции.

Из документации Hive как работать с аналитическими и оконными функциями не особо понятно, поэтому стоит смотреть в документации к другим БД или подобных статьях (не забывая учитывать специфику Hive QL).


