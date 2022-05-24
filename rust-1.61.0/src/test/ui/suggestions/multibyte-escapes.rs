// Regression test for #87397.

fn main() {
    b'µ';
    //~^ ERROR: non-ASCII character in byte constant
    //~| HELP: if you meant to use the unicode code point for 'µ', use a \xHH escape
    //~| NOTE: byte constant must be ASCII

    b'字';
    //~^ ERROR: non-ASCII character in byte constant
    //~| NOTE: this multibyte character does not fit into a single byte
    //~| NOTE: byte constant must be ASCII

    b"字";
    //~^ ERROR: non-ASCII character in byte constant
    //~| HELP: if you meant to use the UTF-8 encoding of '字', use \xHH escapes
    //~| NOTE: byte constant must be ASCII
}
