#![feature(generic_const_exprs)]
#![allow(incomplete_features)]

trait Foo<const N: usize> {
    fn test(&self) -> [u8; N + 1];
}

impl<const N: usize> Foo<N> for () {
    fn test(&self) -> [u8; N + 1] {
        [0; N + 1]
    }
}

fn use_dyn<const N: usize>(v: &dyn Foo<N>) where [u8; N + 1]: Sized {
    assert_eq!(v.test(), [0; N + 1]);
}

fn main() {
    // FIXME(generic_const_exprs): Improve the error message here.
    use_dyn(&());
    //~^ ERROR type annotations needed
}
