int foo(int n)
{
	if (n <= 0) {
		return 1;
	}
	foo(n - 1);
}

int main()
{
	int i;
	int j;
	j = 1;
	i = 0;
	while (i < 10) {
		if (i / 2 == 0) {
			j = j + foo(i);
		}
		if (i / 2 != 0) {
			j = j + foo(i);
		}
		i = i + 1;
	}
	print(j);
}