class Solution {
    public long maxAlternatingSum(int[] nums) {
        for (int i = 0; i < nums.length; i++) {
            nums[i] = Math.abs(nums[i]);
        }

        Arrays.sort(nums);

        int n = nums.length;
        long minus = 0;
        long total = 0;

        for (int i = 0; i < n; i++) {
            long square = (long) nums[i] * nums[i];

            if (i < n / 2) {
                minus += square;
            } else {
                total += square;
            }
        }

        return total - minus;
    }
}
