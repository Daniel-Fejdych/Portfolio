using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class Spawner : MonoBehaviour
{
    // Start is called before the first frame update
    void Awake()
    {
        
    }
    public float speed = 5;
    private int index1 = 0;
    private int index2 = 0;
    public GameObject currPrefab;

    public GameObject player;
    // Update is called once per frame
    void Update()
    {
        //code to move the player
        var move = new Vector3(player.transform.position.x, player.transform.position.y, 0);
        transform.position += move * speed * Time.deltaTime;
        if (Mathf.Abs(transform.position.x) > 100)
        {
            transform.position = new Vector3(-transform.position.x, transform.position.y, 0);
        }
        if (Mathf.Abs(transform.position.y) > 50)
        {
            transform.position = new Vector3(transform.position.x, -transform.position.y, 0);
        }
        //outer 6 frame loop
        index1++;
        if (index1 > 6)
        {
            //inner 20(*6 from outer, 120 frame repeat) frame loop
            index2++;
            if (index2 < 11)
            {
                var num = Random.Range(-0.0f, 0.0f);//proboblly unnecessary
                //create missile
                GameObject p = (GameObject)Instantiate(currPrefab, new Vector3(transform.position.x, transform.position.y, 0), Quaternion.identity);
                //set missile innards
                p.GetComponent<EnemyMovement>().speed = 1;
                p.GetComponent<EnemyMovement>().hRadius = num - transform.position.x + player.transform.position.x;
                p.GetComponent<EnemyMovement>().vRadius = num - transform.position.y + player.transform.position.y;
                p.GetComponent<EnemyMovement>().hDisp = num;
                p.GetComponent<EnemyMovement>().vDisp = num;
            }
            else if (index2 > 20)
            {
                index2 = 0;
            }
            index1 = 0;
        }
    }
}
