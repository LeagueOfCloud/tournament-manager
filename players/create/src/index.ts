import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import mariadb, { Connection } from "mariadb";

type CreateEvent = {
    name: string;
    avatar_bytes: string;
    discord_id?: string;
    team_id: number;
    team_role: string;
}

const s3Client = new S3Client();

const insertPlayer = `
    INSERT INTO players (name, avatar_url, discord_id, team_id, team_role)
    VALUES (?, ?, ?, ?, ?)
`;

export const handler = async (event: CreateEvent): Promise<string> => {
    const { name, avatar_bytes, discord_id, team_id, team_role } = event;

    let connection: Connection;

    try {
        const bucketName = process.env.BUCKET_NAME;
        if (!bucketName) {
            throw new Error('BUCKET_NAME environment variable is not set');
        }

        connection = await mariadb.createConnection({
            host: process.env.DB_HOST,
            port: parseInt(process.env.DB_PORT),
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME
        });

        const fileName = `avatars/${name}.idk`;

        const command = new PutObjectCommand({
            Bucket: bucketName,
            Key: fileName,
            Body: avatar_bytes
        });

        await s3Client.send(command);

        const player = [
            name,
            `https://lockout.nemika.me/${fileName}`,
            discord_id,
            team_id,
            team_role
        ];

        const result = await connection.query(insertPlayer, player);

        return `Player created: ${result.insertId}`
    } catch (error) {
        console.error(`Failed to create player: ${name} with error: ${error instanceof Error ? error.message : 'Unknown error'}`)
        throw error
    } finally {
        connection.end();
    }
}

handler({
    name: "name",
    avatar_bytes: "avatar_bytes",
    discord_id: "discord_id",
    team_id: 69,
    team_role: "TOP"
});
