int foo(int n)
{
	if (n <= 0) {
		return 1;
	}
	return foo(n - 1);
}

int main()
{
	int i;
	int j;
	j = 1;
	i = 0;
	while (i < 11) {
		if ((i - (i / 2)) != 0) {
			j = j + foo(i);
		}
		if ((i - (i / 2)) != 0) {
			j = j + foo(i);
		}
		i = i + 1;
	}
	print(j - 1);
}