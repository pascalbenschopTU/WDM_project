rs.initiate(
    {
        _id: "order_rs-shard-03", 
        version: 1, 
        members: [ 
            { _id: 0, host: "order-shard03-a:27136" },
            { _id: 1, host: "order-shard03-b:27137" },
            { _id: 2, host: "order-shard03-c:27138" },
        ] 
    }
)