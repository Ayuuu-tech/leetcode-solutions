/**
 * Definition for singly-linked list.
 * public class ListNode {
 *     int val;
 *     ListNode next;
 *     ListNode() {}
 *     ListNode(int val) { this.val = val; }
 *     ListNode(int val, ListNode next) { this.val = val; this.next = next; }
 * }
 */

class Solution {
    public ListNode deleteDuplicates(ListNode head) {
        ListNode dummy = new ListNode(0);
        dummy.next = head;

        ListNode prev = dummy;
        ListNode temp = head;

        while (temp != null && temp.next != null) {
            if (temp.val == temp.next.val) {
                int duplicate = temp.val;

                while (temp != null && temp.val == duplicate) {
                    temp = temp.next;
                }

                prev.next = temp;
            } else {
                prev = temp;
                temp = temp.next;
            }
        }

        return dummy.next;
    }
}
