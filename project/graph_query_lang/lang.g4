grammar lang;

WHITESPACE: [ \t\r] -> skip;
CHAR: [a-z] | [A-Z] | '_';
DIGIT: [0-9];
NONZERO: [1-9];
ID: CHAR (CHAR | DIGIT)*;

var: CHAR | ID;

STRING: '"' (CHAR | DIGIT | '_')* '"';
INT: NONZERO DIGIT*;
BOOL: 'true' | 'false';

REGEX: '{"' ~[\n]* '"}';
CFG: '{|' ~[\n]* '|}';

string: STRING;
int: DIGIT | INT;
bool: BOOL;
regex: REGEX;
cfg: CFG;

val: string | int | bool | regex | cfg;

lambda:
	| '\\' var (WHITESPACE var)* '->' expr
	| '(' lambda ')';

semigraph:
  | 'set_start' set
  | 'set_final' set
  | 'add_start' set
  | 'add_final' set;

// underscore here to generate correct dot files because of 'graph' is keyword
graph_:
  | var
  | semigraph '(' graph_ ')'
  | graph_ '|>' semigraph
  | 'load' string;

semiset:
  | 'map' lambda
  | 'filter' lambda;

set:
	| var
	| 'get_start' graph_
	| 'get_final' graph_
	| 'get_reachable' graph_
	| 'get_edges' graph_
	| 'get_labels' graph_
	| 'get_vertices' graph_
	| semiset '(' set ')'
	| set '|>' semiset
	| '[' (expr (',' expr)*) ']'
	| '[' expr '..' expr ']'
	| '[' ']';

lang_binop: '&' | '|' | '.';
binop: '&&' | '||' | 'in';
unop: 'not' | '-';

expr:
	| var
	| val
	| graph_
	| set
	| expr lang_binop expr
	| expr '*'
	| expr binop expr
	| unop expr;

EOL: '\n';
stmt: | 'print' expr | 'let' var '=' expr;
prog: EOL* stmt (EOL+ stmt)* EOL* EOF;
