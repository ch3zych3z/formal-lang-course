# Язык запросов к графам

## Описание абстрактного синтаксиса языка

```
prog = List<stmt>

stmt =
    bind of var * expr
  | print of expr

val =
    String of string
  | Int of int
  | Regex of regex
  | CFG of cfg

expr =
    Var of var                   // переменные
  | Val of val                   // константы
  | Set_start of Set<val> * expr // задать множество стартовых состояний
  | Set_final of Set<val> * expr // задать множество финальных состояний
  | Add_start of Set<val> * expr // добавить состояния в множество стартовых
  | Add_final of Set<val> * expr // добавить состояния в множество финальных
  | Get_start of expr            // получить множество стартовых состояний
  | Get_final of expr            // получить множество финальных состояний
  | Get_reachable of expr        // получить все пары достижимых вершин
  | Get_vertices of expr         // получить все вершины
  | Get_edges of expr            // получить все рёбра
  | Get_labels of expr           // получить все метки
  | Map of lambda * expr         // классический map
  | Filter of lambda * expr      // классический filter
  | Load of path                 // загрузка графа
  | Intersect of expr * expr     // пересечение языков
  | Concat of expr * expr        // конкатенация языков
  | Union of expr * expr         // объединение языков
  | Star of expr                 // замыкание языков (звезда Клини)
  | Smb of expr                  // единичный переход
  | Pipe of expr * expr          // pipe как в Ocaml или F#

lambda =
  | Abs of List<var> * expr
```

## Описание конкретного синтаксиса

```
whitespace := [ \t\r]+ -> skip
char := [a-z] | [A-Z]
digit := [0-9]
nonzero_digit := [1-9]
id = char (char | digit)*

var := char | id

string := '"' (char | digit | '_')* '"'
symbol := char | digit | '_' | '*' | '+' | '.'
int := nonzero_digit digit+
bool := 'true' | 'false'

regex := '{"' symbol* '"}'
cfg := '{|' symbol* '|}'

val := string | int | bool | regex | cfg

lambda :=
  | '\' var (whitespace var)* '->' expr
  | '(' lambda ')'

path := '"' (char | digit | '_' | '/' | '.')* '"'

semigraph :=
  | 'set_start' set
  | 'set_final' set
  | 'add_start' set
  | 'add_final' set

graph :=
  | var
  | semigraph graph
  | graph '|>' semigraph
  | 'load' path

semiset :=
  | 'map' lambda
  | 'filter' lambda

set :=
  | var
  | 'get_start' graph
  | 'get_final' graph
  | 'get_reachable' graph
  | 'get_edges' graph
  | 'get_labels' graph
  | 'get_vertices' graph
  | semiset set
  | set '|>' semiset
  | '[' (expr (',' expr)*)? ']'
  | '[' expr '..' expr ']'

lang_binop := '&' | '|' | '.'
binop := '&&' | '||' | 'in'
unop := 'not' | '-'

expr :=
  | var
  | val
  | graph
  | set
  | expr lang_binop expr
  | expr '*'
  | expr binop expr
  | unop expr

stmt :=
  | 'print' expr
  | 'let' var '=' expr

prog := (stmt ('\n'+ stmt)*)? EOF
```

## Примеры скриптов

### Загрузка графа и назначение стартовых и финальных вершин

```
let graph = load "filename"
let vertices = get_vertices graph
let graph = graph |> set_start vertices |> set_final [0..3]
```

### Объявление регулярного выражения

```
let regex1 = {"a+"}
let regex2 = {"b*"}
let regex = regex1 | regex2
```

### Объявление КС-грамматики

```
let cfg = {| S -> a S b S | S -> epsilon |}
```

### Запросы

```
let regex_intersection = graph & regex
let cfg_intersection = graph & cfg

print regex_intersection
print cfg_intersection
```
