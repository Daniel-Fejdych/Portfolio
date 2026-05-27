using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class EnemyMovement : MonoBehaviour
{

    public float speed = 5;
    public float hRadius = 1;
    public float vRadius = 1;
    public float hDisp = 0;
    public float vDisp = 0;
    private float startTime;
    private float currentTime;
    void Awake()
    {
        startTime = Time.time;
    }
    // Update is called once per frame
    void FixedUpdate()
    {
        currentTime = Time.time - startTime;
        var horizontal = hRadius * Mathf.Sin(currentTime * speed + hDisp);
        var vertical = vRadius * Mathf.Cos(currentTime * speed + vDisp);
        var move = new Vector3(horizontal, vertical, 0);
        transform.position += move * Time.deltaTime * speed;
        if (currentTime > 10)
        {
            Destroy(gameObject);
        }
    }
}
