int add(int a0, int a1)
{
    return a0 + a1;
}

int sub(int a0, int a1)
{
    return a0 - a1;
}

int mult(int a0, int a1)
{
    return a0 * a1;
}

int main()
{
    int x0;
    int x1;
    int x2;
    int x3;
    int x4;
    int x5;
    x0 = 5;
    x1 = 10;
    x2 = 15;
    x3 = 15;
    x5 = add(sub(x1, x1), mult(x2, x3)) + sub(mult(x2, x3),
                          add(x2, x3)) + 1;
    print(x5);
}