class Solution {
    public void nextPermutation(int[] nums) {
        int breaks = -1;
        for(int i = nums.length-2 ; i>=0 ; i-- ){
            if(nums[i+1]>nums[i]){
                breaks = i;
                break;
            }
        }
        if(breaks!=-1){
        for(int i = nums.length-1 ; i>breaks; i-- ){
            if(nums[i] > nums[breaks]){
                int temp = nums[i];
                nums[i] = nums[breaks];
                nums[breaks] = temp;
                break;
            }
        }
        }
        int i = breaks+1;
        int j = nums.length-1;
        while(i<j){
            int temp = nums[i];
            nums[i] = nums[j];
            nums[j] = temp;
            i++;
            j--;
        }
    }
}