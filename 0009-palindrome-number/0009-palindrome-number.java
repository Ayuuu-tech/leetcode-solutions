class Solution {
    public boolean isPalindrome(int x) {
        int m = x;
        int n = 0;
        int k = 1;
        while(x>0){
            int c = x%10;
            n= n*10 + c;
            x/=10;
        }
        return n == m;
    }
}