int pow(int a, int b)
{
	if (b <= 0) {
		return a;
	}
	return a * pow(a, b - 1);
}

int main()
{
	int x0;
	int x1;
	int x2;
	x0 = 5;
	x1 = 10;
	x2 = pow(x0, x1);
	print(x2);
}