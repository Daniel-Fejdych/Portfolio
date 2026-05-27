using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

public class PlayerController : MonoBehaviour 
{
    public float speed = 5;
    public int maxHealth = 20;
    public int currentHealth;
    private int dmgTimeCounter = 60;

    public HealthBar healthBar;

    void Start()
    {
        currentHealth = maxHealth;
        healthBar.SetMaxHealth(maxHealth);
    }

    void OnTriggerStay2D(Collider2D other)
    {
        if (dmgTimeCounter > 59)
        {
            TakeDamage(1);
            dmgTimeCounter = 0;
            Destroy(other.gameObject);
        }
    }

    void TakeDamage(int damage)
    {
        currentHealth -= damage;
        healthBar.SetHealth(currentHealth);
        if(currentHealth < 1)
        {
            SceneManager.LoadScene("SampleScene");
        }

    }
    // Update is called once per frame
    void Update()
    {
        var move = new Vector3(Input.GetAxis("Horizontal"), Input.GetAxis("Vertical"), 0);
        transform.position += move * speed * Time.deltaTime;

        if(dmgTimeCounter<60)
        {
            dmgTimeCounter++;
        }
    }
}
